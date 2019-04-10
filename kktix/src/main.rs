extern crate regex;
extern crate reqwest;
extern crate serde;
#[macro_use]
extern crate serde_derive;
#[macro_use]
extern crate serde_json;
extern crate toml;
extern crate urlparse;

// --- external ---
use reqwest::{
    Client, Error as ReqwestError, Response,
    header::HeaderMap,
};
use serde_json::Value;

#[derive(Debug)]
enum KktixError {
    AccountError,
    ParamError,
    TokenError,
    ReqwestError(ReqwestError),
}

#[derive(Clone)]
struct Kktix {
    client: Client,
    headers: HeaderMap,
}


#[derive(Deserialize)]
struct Conf {
    account: Account,
    ticket: Ticket,
}

#[derive(Deserialize)]
struct Account {
    thread: u32,
    username: String,
    password: String,
}

#[derive(Deserialize)]
struct Ticket {
    id: u32,
    quantity: u32,
    event_id: String,
}

fn reqwest_get(client: &Client, url: &str, headers: HeaderMap) -> Result<Response, KktixError> {
    match client.get(url).headers(headers).send() {
        Ok(resp) => Ok(resp),
        Err(e) => Err(KktixError::ReqwestError(e))
    }
}

fn reqwest_post_form(client: &Client, url: &str, headers: HeaderMap, form: &[(&str, &str)]) -> Result<Response, KktixError> {
    match client.post(url).headers(headers).form(form).send() {
        Ok(resp) => Ok(resp),
        Err(e) => Err(KktixError::ReqwestError(e))
    }
}

fn reqwest_post_json(client: &Client, url: &str, headers: HeaderMap, json: &Value) -> Result<Response, KktixError> {
    match client.post(url).headers(headers).json(json).send() {
        Ok(resp) => Ok(resp),
        Err(e) => Err(KktixError::ReqwestError(e))
    }
}

fn to_json(mut resp: Response) -> Result<Value, KktixError> {
    match resp.json() {
        Ok(json) => Ok(json),
        Err(e) => Err(KktixError::ReqwestError(e)),
    }
}

fn set_cookie(headers: &HeaderMap) -> HeaderMap {
    let cookies = headers
        .iter()
        .filter(|&(k, _)| k == "set-cookie")
        .map(|(_, v)| v.to_str().unwrap().split(';').next().unwrap())
        .collect::<Vec<_>>()
        .join("; ");

    let mut headers = HeaderMap::new();
    headers.insert("cookie", cookies.parse().unwrap());
    headers
}

fn solve_question(question: &str) -> String {
    // --- external ---
    use regex::Regex;

    for re in [
        Regex::new(r"(.+)").unwrap(),
        Regex::new(r"「(.+)」").unwrap()
    ].iter() { if let Some(caps) = re.captures(question) { return caps[1].to_owned(); } }

    panic!("unsupported question: {}", question)
}

fn load_conf() -> Conf {
    // --- std ---
    use std::{
        fs::File,
        io::Read,
    };

    match File::open("conf.toml") {
        Ok(mut f) => {
            let mut s = String::new();
            f.read_to_string(&mut s).unwrap();

            toml::from_str(&s).unwrap()
        }
        Err(e) => panic!("{:?}", e)
    }
}

impl Kktix {
    fn sign_in(username: &str, password: &str) -> Result<Kktix, KktixError> {
        // --- std ---
        use std::time::Duration;
        // --- external ---
        use reqwest::{ClientBuilder, RedirectPolicy};

        let client = ClientBuilder::new()
            .danger_accept_invalid_certs(true)
            .danger_accept_invalid_hostnames(true)
            .gzip(true)
            .redirect(RedirectPolicy::none())
            .timeout(Duration::from_secs(3))
            .build()
            .unwrap();
        let headers = {
            let headers = set_cookie(reqwest_get(
                &client,
                "https://kktix.com/users/sign_in",
                HeaderMap::new())?.headers());
            let authenticity_token = {
                let cookies = headers.get("cookie")
                    .unwrap()
                    .to_str()
                    .unwrap();

                urlparse::unquote(&cookies[cookies.find("XSRF-TOKEN=").unwrap() + 11..cookies.len()]).unwrap()
            };

            set_cookie(reqwest_post_form(
                &client,
                "https://kktix.com/users/sign_in",
                headers.clone(),
                &[
                    ("utf8", "✓"),
                    ("authenticity_token", &authenticity_token),
                    ("user[login]", username),
                    ("user[password]", password),
                    ("user[remember_me]", "0"),
                    ("commit", "Sign In"),
                ])?.headers())
        };

        if reqwest_get(&client, "https://kktix.com/users/edit", headers.clone())?.status() == 302 { Err(KktixError::AccountError) } else { Ok(Kktix { client, headers }) }
    }

    fn register_info(&self, event_id: &str) -> Result<(String, String), KktixError> {
        let register_info = to_json(reqwest_get(&self.client, &format!("https://kktix.com/g/events/{}/register_info", event_id), self.headers.clone())?)?;
        let question = register_info["ktx_captcha"]["question"].as_str().unwrap();

        Ok((
            solve_question(question),
            register_info["order"]["price_currency"]
                .as_str()
                .unwrap()
                .to_owned()
        ))
    }

    fn queue(&self, ticket: &Ticket) -> Result<(), KktixError> {
        // --- std ---
        use std::{
            thread::sleep,
            time::Duration,
        };

        let cookies = self.headers.get("cookie")
            .unwrap()
            .to_str()
            .unwrap();
        let authenticity_token = &cookies[cookies.find("XSRF-TOKEN=").unwrap() + 11..cookies.len()];
        let (answer, currency) = self.register_info(&ticket.event_id)?;

        if let Some(token) = to_json(reqwest_post_json(
            &self.client,
            &format!("https://queue.kktix.com/queue/{}?authenticity_token={}", ticket.event_id, authenticity_token),
            self.headers.clone(),
            &json!({
                "agreeTerm": true,
                "currency": currency,
                "custom_captcha": answer,
                "recaptcha": json!({}),
                "tickets": [json!({
                    "id": ticket.id,
                    "quantity": ticket.quantity,
                    "invitationCodes": [],
                    "member_code": "",
                    "use_qualification_id": Value::Null
                })]
            }),
        )?)?.get("token") {
            sleep(Duration::from_millis(200));

            if let Some(param) = to_json(reqwest_get(&self.client, &format!("https://queue.kktix.com/queue/token/{}", token.as_str().unwrap()), HeaderMap::new())?)?.get("to_param") {
                println!("https://kktix.com/events/{}/registrations/{}#", ticket.event_id, param.as_str().unwrap());
                Ok(())
            } else { Err(KktixError::ParamError) }
        } else { Err(KktixError::TokenError) }
    }
}

fn main() {
    // --- std ---
    use std::{
        sync::{
            Arc, Mutex,
            mpsc::{TryRecvError, channel},
        },
        thread::spawn,
    };

    let conf = load_conf();
    match Kktix::sign_in(&conf.account.username, &conf.account.password) {
        Ok(kktix) => {
            let (tx, rx) = channel();
            let tx = Arc::new(Mutex::new(tx));
            let rx = Arc::new(Mutex::new(rx));
            let kktix = Arc::new(kktix);
            let ticket = Arc::new(conf.ticket);

            for i in 0..conf.account.thread {
                let tx = tx.clone();
                let rx = rx.clone();
                let thread = conf.account.thread;
                let kktix = kktix.clone();
                let ticket = ticket.clone();

                spawn(move || loop {
                    println!("thread {} start", i);
                    match rx.lock().unwrap().try_recv() {
                        Ok(_) | Err(TryRecvError::Disconnected) => {
                            println!("thread {} end", i);
                            break;
                        }
                        Err(TryRecvError::Empty) => ()
                    }

                    match kktix.queue(&ticket) {
                        Ok(_) => for _ in 0..thread { tx.lock().unwrap().send(()).unwrap(); }
                        Err(e) => println!("{:?}", e)
                    }
                });
            }
        }
        Err(e) => println!("{:?}", e)
    }

    loop {}
}
