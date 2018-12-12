#[macro_use]
extern crate lazy_static;
extern crate regex;
extern crate reqwest;

// --- std ---
use std::{
    fs::File,
    io::{Read, Write, stdin, stdout},
    process::Command,
    sync::{Arc, Mutex},
    thread,
};

// --- external ---
use regex::Regex;
use reqwest::{
    Client,
    ClientBuilder,
    header::{COOKIE, SET_COOKIE, HeaderMap, HeaderValue},
};

lazy_static! { static ref REGEX: Regex = Regex::new(r"alert\('(.+?)'\)").unwrap(); }

struct User {
    name: String,
    session: Client,
}

impl User {
    fn new(name: String) -> Self {
        User {
            name,
            session: Client::new(),
        }
    }

    fn save_cookie(&mut self, cookie: HeaderValue) {
        self.session = {
            let mut headers = HeaderMap::new();
            headers.insert(COOKIE, cookie);
            ClientBuilder::new()
                .danger_accept_invalid_certs(true)
                .danger_accept_invalid_hostnames(true)
                .default_headers(headers)
                .build()
                .unwrap()
        };
    }

    fn get_captcha(&mut self, retry: bool) -> String {
        let mut resp = self.session
            .get("http://www.xinqiyang.cn/Home/login/verify")
            .send()
            .unwrap();

        if !retry {
            self.save_cookie(resp.headers()
                .get(SET_COOKIE)
                .unwrap()
                .to_owned()
            );
        }

        let mut captcha = vec![];
        resp.copy_to(&mut captcha).unwrap();

        let mut f = File::create("captcha.png").unwrap();
        f.write(&captcha).unwrap();

        Command::new("open")
            .arg("captcha.png")
            .spawn()
            .unwrap();


        print!("User {}, captcha -> ", self.name);
        stdout().flush().unwrap();

        let mut captcha = String::new();
        stdin().read_line(&mut captcha).unwrap();
        captcha
    }

    fn sign_in(&mut self) -> bool {
        let mut captcha = self.get_captcha(false);
        loop {
            let mut resp = self.session.post("http://www.xinqiyang.cn/Home/Login/logincl").form(&[
                ("ip", "8.8.8.8"),
                ("account", &self.name),
                ("password", "171201"),
                ("verCode", captcha.trim()),
            ]).send().unwrap();

            let text = resp.text().unwrap();
            if let Some(captures) = REGEX.captures(text.trim()) {
                let resp = captures.get(1).unwrap().as_str();
                println!("User {}, {}", self.name, resp);

                match resp {
                    "验证码错误，请刷新验证码！" => captcha = self.get_captcha(true),
                    _ => println!("{}", resp),
                }
            } else {
                if text.contains("系统升级中,请于09:00-22:00访问!") {
                    println!("系统升级中,请于09:00-22:00访问!");
                    return false;
                } else {
                    println!("User {}, sign in succeed", self.name);
                    return true;
                }
            }
        }
    }

    fn rush(self) {
        let user = Arc::new(self);
        let keep_rush = Arc::new(Mutex::new(true));
        while *keep_rush.lock().unwrap() {
            let mut handlers = vec![];
            for i in 1u8..=40 {
                let user = Arc::clone(&user);
                let keep_rush = Arc::clone(&keep_rush);
                let handler = thread::spawn(move || {
                    loop {
                        match user.session.get(&format!("http://www.xinqiyang.cn/Home/Myuser/grab/name/{}", i)).send() {
                            Ok(mut resp) => {
                                let text = resp.text().unwrap();
                                let resp = REGEX.captures(text.trim())
                                    .unwrap()
                                    .get(1)
                                    .unwrap()
                                    .as_str();

                                println!("User {} at task {}, {}", user.name, i, resp);

                                if resp == "预约币不足，请先充值预约币！" || resp == "一天只能抢单两次！" { *keep_rush.lock().unwrap() = false; }
                                break;
                            }
                            Err(_) => ()
                        }
                    }
                });

                handlers.push(handler);
            }

            for handler in handlers { handler.join().unwrap(); }
        }
    }
}

fn main() {
    let mut users = vec![];

    let accounts = {
        let mut accounts = String::new();
        File::open("accounts.txt")
            .unwrap()
            .read_to_string(&mut accounts)
            .unwrap();

        accounts
    };
    for account in accounts.lines() {
        let mut user = User::new(account.to_owned());
        if !user.sign_in() { return; };
        users.push(user);
    }

    let mut handlers = vec![];
    for user in users {
        let handler = thread::spawn(move || user.rush());

        handlers.push(handler);
    }

    for handler in handlers { handler.join().unwrap(); }
}
