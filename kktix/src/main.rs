extern crate reqwest;
extern crate select;

// --- external ---
use reqwest::{
    Client,
    header::HeaderMap,
};

fn default_client() -> Client {
    // --- std ---
    use std::time::Duration;
    // --- external ---
    use reqwest::ClientBuilder;

    ClientBuilder::new()
        .danger_accept_invalid_certs(true)
        .danger_accept_invalid_hostnames(true)
        .gzip(true)
        .timeout(Duration::from_secs(3))
        .build()
        .unwrap()
}

struct Kktix(Client);

impl Kktix {
    fn sign_in(username: &str, password: &str) -> Kktix {
        let client = default_client();
        let (headers, csrf) = {
            let cookie;
            let csrf;
            loop {
                if let Ok(mut resp) = client.get("https://kktix.com/users/sign_in").send() {
                    if let Ok(text) = resp.text() {
                        cookie = resp.headers()[reqwest::header::SET_COOKIE].to_owned();
                        csrf = {
                            // --- external ---
                            use select::{
                                document::Document,
                                predicate::Name,
                            };

                            let document = Document::from(text.as_str());
                            document.find(Name("meta"))
                                .skip(13)
                                .next()
                                .unwrap()
                                .attr("content")
                                .unwrap()
                                .to_owned()
                        };

                        break;
                    }
                }
            }

            println!("{:?}, {}", cookie, csrf);

            let mut headers = HeaderMap::new();
            headers.insert(reqwest::header::COOKIE, cookie);
            println!("{:?}", headers);

            (headers, csrf)
        };

        loop {
            if let Ok(mut resp) = client.post("https://kktix.com/users/sign_in")
                .form(&[
                    ("utf8", "✓"),
                    ("authenticity_token", &csrf),
                    ("user[login]", username),
                    ("user[password]", password),
                    ("user[remember_me]", "0"),
                    ("commit", "Sign+In"),
                ])
//                .body(format!(
//                    "utf8=✓&authenticity_token={}&user[login]={}&user[password]={}&user[remember_me]=0&commit=Sign+In",
//                    csrf,
//                    username,
//                    password
//                ))
                .headers(headers.clone())
                .send() {
                println!("{}", resp.text().unwrap());
                println!("{:?}", client.get("https://kktix.com/users/edit").headers(headers.clone()).send().unwrap().url());
                return Kktix(default_client());
            }
        }
    }

//    fn from_cookie(cookie: &str) -> Kktix {
//        let mut headers = HeaderMap::new();
//        headers.insert(COOKIE, cookie.parse().unwrap());
//
//        Kktix(default_client(headers))
//    }
}

fn main() {
    // --- std ---
//    use std::io::{Write, stdin, stdout};
//
//    let cookie = {
//        print!("Cookie: ");
//        stdout().flush().unwrap();
//        let mut s = String::new();
//        stdin().read_line(&mut s).unwrap();
//
//        s.trim().to_owned()
//    };
//
//    let user = Kktix::from_cookie(&cookie);
    let user = Kktix::sign_in("test1234", "test1234");
}
