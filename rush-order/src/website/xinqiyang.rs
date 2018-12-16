// --- std ---
use std::{
    fs::File,
    io::Read,
    sync::{Arc, Mutex},
    thread,
};

// --- external ---
use regex::Regex;
use reqwest::{
    Client,
    header::{COOKIE, SET_COOKIE, HeaderMap},
};

// --- custom ---
use crate::user::User;
use super::{XINQIYANG_CAPTCHA, XINQIYANG_ORDER, XINQIYANG_SIGN_IN};

lazy_static! { static ref REGEX: Regex = Regex::new(r"alert\('(.+?)'\)").unwrap(); }

pub struct XinQiYang {
    name: String,
    session: Client,
}

impl XinQiYang {
    pub fn new(name: &str) -> XinQiYang {
        XinQiYang {
            name: name.to_owned(),
            session: Client::new(),
        }
    }
}

impl User for XinQiYang {
    fn get_captcha(&mut self, retry: bool) -> String {
        let resp = self.session
            .get(XINQIYANG_CAPTCHA)
            .send()
            .unwrap();

        if !retry {
            let mut header = HeaderMap::new();
            header.insert(
                COOKIE,
                resp.headers()
                    .get(SET_COOKIE)
                    .unwrap()
                    .to_owned(),
            );

            <XinQiYang as User>::load_header(&mut self.session, header);
        }

        <XinQiYang as User>::save_read_captcha(&self.name, resp)
    }

    fn sign_in(&mut self) -> bool {
        let mut captcha = self.get_captcha(false);
        loop {
            let mut resp = self.session.post(XINQIYANG_SIGN_IN).form(&[
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
                    "验证码错误，请刷新验证码！" => {
                        captcha = self.get_captcha(true);
                        continue;
                    }
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

    fn load_users() -> Option<Vec<XinQiYang>> {
        let accounts = {
            let mut accounts = String::new();
            File::open("xinqiyang.txt")
                .unwrap()
                .read_to_string(&mut accounts)
                .unwrap();

            accounts
        };

        let mut users = vec![];
        for account in accounts.lines() {
            let mut user = XinQiYang::new(account);
            if !user.sign_in() { return None; };
            users.push(user);
        }

        Some(users)
    }

    fn order(self) {
        let user = Arc::new(self);
        let keep_rush = Arc::new(Mutex::new(true));
        while *keep_rush.lock().unwrap() {
            let mut handlers = vec![];
            for i in 1u8..=40 {
                let user = Arc::clone(&user);
                let keep_rush = Arc::clone(&keep_rush);
                let handler = thread::spawn(move || {
                    loop {
                        match user.session.get(&format!("{}/{}", XINQIYANG_ORDER, i)).send() {
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

    fn rush() {
        if let Some(users) = XinQiYang::load_users() {
            let mut handlers = vec![];
            for user in users {
                let handler = thread::spawn(|| user.order());
                handlers.push(handler);
            }

            for handler in handlers { handler.join().unwrap(); }
        }
    }
}
