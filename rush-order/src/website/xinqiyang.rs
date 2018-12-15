// --- std ---
use std::{
    fs::File,
    io::Write,
    sync::{Arc, Mutex},
    thread,
};

// --- external ---
use regex::Regex;
use reqwest::{
    Client,
    header::SET_COOKIE,
};

// --- custom ---
use crate::user::{User, save_captcha, load_cookie};
use super::{XINQIYANG_CAPTCHA, XINQIYANG_ORDER, XINQIYANG_SIGN_IN};

lazy_static! { static ref REGEX: Regex = Regex::new(r"alert\('(.+?)'\)").unwrap(); }

pub struct XinQiYang {
    name: String,
    session: Client,
}

impl User<XinQiYang> for XinQiYang {
    fn get_captcha(&mut self, retry: bool) -> String {
        let mut resp = self.session
            .get(XINQIYANG_CAPTCHA)
            .send()
            .unwrap();

        if !retry {
            load_cookie(
                session,
                resp.headers()
                    .get(SET_COOKIE)
                    .unwrap()
                    .to_owned(),
            );
        }

        save_captcha(resp)
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
}

impl XinQiYang {
    fn new(name: &str) -> XinQiYang {
        XinQiYang {
            name: name.to_owned(),
            session: Client::new(),
        }
    }
}