// --- std ---
use std::{
    fs::File,
    io::Read,
    sync::{Arc, Mutex},
    thread,
};

// --- external ---
use reqwest::{
    Client,
    header::{COOKIE, SET_COOKIE, HeaderMap},
};
use serde_json::Value;

// --- custom ---
use crate::user::User;
use super::{LIUYUZ_CAPTCHA, LIUYUZ_ORDER, LIUYUZ_SIGN_IN};

pub struct LiuYuZ {
    name: String,
    session: Client,
}

impl LiuYuZ {
    pub fn new(name: &str) -> LiuYuZ {
        LiuYuZ {
            name: name.to_owned(),
            session: Client::new(),
        }
    }
}

impl User for LiuYuZ {
    fn get_captcha(&mut self, retry: bool) -> String {
        let resp = self.session
            .get(LIUYUZ_CAPTCHA)
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
            header.insert("X-Requested-With", "XMLHttpRequest".parse().unwrap());

            <LiuYuZ as User>::load_header(&mut self.session, header);
        }

        <LiuYuZ as User>::save_read_captcha(&self.name, resp)
    }

    fn sign_in(&mut self) -> bool {
        let mut captcha = self.get_captcha(false);
        loop {
            let mut resp = self.session.post(LIUYUZ_SIGN_IN).form(&[
                ("lang", "1"),
                ("user_code", &self.name),
                ("pass", "ly171201"),
                ("verify", captcha.trim()),
            ]).send().unwrap();

            let text = resp.text().unwrap();
            match text.trim() {
                "<script>window.location.href=\"/\";</script>" => {
                    println!("User {}, sign in succeed", self.name);
                    return true;
                }
                "<script>self.location=document.referrer;</script>" => {
                    println!("Please retry.");
                    captcha = self.get_captcha(true);
                    continue;
                }
                _ => {
                    println!("每天22点网站自动关闭维护, 早上9点正式开网.");
                    return false;
                }
            }
        }
    }

    fn load_users() -> Option<Vec<LiuYuZ>> {
        let accounts = {
            let mut accounts = String::new();
            File::open("liuyuz.txt")
                .unwrap()
                .read_to_string(&mut accounts)
                .unwrap();

            accounts
        };

        let mut users = vec![];
        for account in accounts.lines() {
            let mut user = LiuYuZ::new(account);
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
                        match user.session
                            .post(LIUYUZ_ORDER)
                            .form(&[("type", "1")])
                            .send() {
                            Ok(mut resp) => {
                                let resp: Value = serde_json::from_str(&resp.text().unwrap()).unwrap();
                                let info = resp["info"].as_str().unwrap();
                                println!("User {} at task {}, {}", user.name, i, info);

                                if info == "预约币不足，请先充值预约币！" || info == "每人每天最多抢两单" { *keep_rush.lock().unwrap() = false; }
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
        if let Some(users) = LiuYuZ::load_users() {
            let mut handlers = vec![];
            for user in users {
                let handler = thread::spawn(|| user.order());
                handlers.push(handler);
            }

            for handler in handlers { handler.join().unwrap(); }
        }
    }
}
