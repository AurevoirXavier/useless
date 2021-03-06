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
use std::io::Write;

#[derive(Debug)]
enum KktixError {
    AccountError,
    AnswerError,
    TokenError,
    Exit(String),
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
    thread: usize,
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

fn get_csrf(headers: &HeaderMap) -> String {
    let cookies = headers.get("cookie")
        .unwrap()
        .to_str()
        .unwrap();

    cookies[cookies.find("XSRF-TOKEN=").unwrap() + 11..cookies.len()].to_owned()
}

fn solve_question(question: &str) -> String {
    // --- std ---
    use std::io::{stdin, stdout};
    // --- external ---
    use regex::Regex;

    if question.is_empty() { return String::new(); }

    for re in [
        Regex::new(r"「(.+?)」").unwrap(),
        Regex::new(r"“(.+?)”").unwrap(),
    ].iter() { if let Some(caps) = re.captures(question) { return caps[1].to_owned(); } }

    print!("Q: {}\nA: ", question);
    stdout().flush().unwrap();
    let mut s = String::new();
    stdin().read_line(&mut s).unwrap();

    s.trim().to_owned()
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
            .timeout(Duration::from_secs(5))
            .build()
            .unwrap();
        let headers = {
            let headers = set_cookie(reqwest_get(
                &client,
                "https://kktix.com/users/sign_in",
                HeaderMap::new())?.headers());

            set_cookie(reqwest_post_form(
                &client,
                "https://kktix.com/users/sign_in",
                headers.clone(),
                &[
                    ("utf8", "✓"),
                    ("authenticity_token", &urlparse::unquote(get_csrf(&headers)).unwrap()),
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
        let status = register_info["inventory"]["registerStatus"].as_str().unwrap();

        if status == "IN_STOCK" {
            let question = if let Some(question) = register_info["ktx_captcha"].get("question") { question.as_str().unwrap() } else { "" };
            Ok((
                solve_question(question),
                register_info["order"]["price_currency"]
                    .as_str()
                    .unwrap()
                    .to_owned()
            ))
        } else {
            println!("{}", status);
            self.register_info(event_id)
        }
    }

    fn queue(&self, ticket: &Ticket, answer: &str, currency: &str) -> Result<String, KktixError> {
        let result = to_json(reqwest_post_json(
            &self.client,
            &format!("https://queue.kktix.com/queue/{}?authenticity_token={}", ticket.event_id, get_csrf(&self.headers)),
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
        )?)?;

        if let Some(token) = result.get("token") { Ok(token.as_str().unwrap().to_owned()) } else {
            let result = result["result"].as_str().unwrap();
            if result == "CAPTCHA_WRONG_ANSWER" { Err(KktixError::AnswerError) } else {
                println!("{}", result);
                Err(KktixError::TokenError)
            }
        }
    }

    fn link(&self, event_id: &str, token: &str) -> Result<String, KktixError> {
        loop {
            if let Ok(resp) = reqwest_get(&self.client, &format!("https://queue.kktix.com/queue/token/{}", token), HeaderMap::new()) {
                let result = to_json(resp).unwrap();

                if let Some(param) = result.get("to_param") {
                    let link = format!("https://kktix.com/events/{}/registrations/{}#", event_id, param.as_str().unwrap());
                    println!("{}", link);

                    return Ok(link);
                }

                if let Some(result) = result.get("result") {
                    if result.as_str().unwrap() == "not_found" { continue; }
                    println!("{:?}", result);
                }

                return Err(KktixError::Exit(result.to_string()));
            }
        }
    }
}

fn order_ticket() -> Result<(), KktixError> {
    // --- std ---
    use std::{
        fs::{File, OpenOptions},
        path::Path,
        sync::{
            Arc, Mutex,
            mpsc::{TryRecvError, channel},
        },
        thread::spawn,
    };

    let Conf { account, ticket } = load_conf();
    let thread = account.thread;
    let kktix = Kktix::sign_in(&account.username, &account.password)?;
    let (answer, currency) = kktix.register_info(&ticket.event_id)?;
    let kktix = Arc::new(kktix);
    let ticket = Arc::new(ticket);
    let f = {
        let path = Path::new("tickets.txt");
        let f = if !path.is_file() { File::create(path).unwrap() } else {
            OpenOptions::new()
                .write(true)
                .open(path)
                .unwrap()
        };

        Arc::new(Mutex::new(f))
    };

    let (tx, rx) = channel();
    let tx = Arc::new(Mutex::new(tx));
    let rx = Arc::new(Mutex::new(rx));

    let mut handlers = vec![];
    for i in 1..=thread {
        let answer = answer.clone();
        let currency = currency.clone();
        let kktix = kktix.clone();
        let ticket = ticket.clone();
        let f = f.clone();

        let tx = tx.clone();
        let rx = rx.clone();

        handlers.push(spawn(move || loop {
            println!("thread {} working", i);
            match rx.lock().unwrap().try_recv() {
                Ok(_) | Err(TryRecvError::Disconnected) => {
                    println!("thread {} end", i);
                    break;
                }
                Err(TryRecvError::Empty) => ()
            }

            match kktix.queue(&ticket, &answer, &currency) {
                Ok(token) => {
                    for _ in 0..thread { tx.lock().unwrap().send(()).unwrap(); }

                    match kktix.link(&ticket.event_id, &token) {
                        Ok(link) => {
                            let mut f = f.lock().unwrap();
                            f.write((link + "\n").as_bytes()).unwrap();
                            f.sync_all().unwrap();
                            f.flush().unwrap();
                        }
                        Err(KktixError::Exit(result)) => println!("{}, thread {} end", result, i),
                        _ => unreachable!()
                    }

                    break;
                }
                Err(e) => match e {
                    KktixError::AnswerError => {
                        println!("wrong answer {}, thread {} end", answer, i);
                        break;
                    }
                    KktixError::TokenError => (),
                    _ => println!("{:?}", e)
                }
            }
        }));
    }
    for handler in handlers { handler.join().unwrap(); }

    Ok(())
}

fn main() { if let Err(e) = order_ticket() { println!("{:?}", e); } }
