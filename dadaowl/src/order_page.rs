// --- std ---
use std::{
    process::Command,
    sync::Mutex,
    thread::sleep,
    time::Duration,
};

// --- external ---
use regex::Regex;
use select::{
    document::Document,
    predicate::{Attr, Class, Name, Predicate},
};

// --- custom ---
use super::vanguard::VANGUARD;

lazy_static! { static ref COUNT: Mutex<u32> = Mutex::new(0); }

pub struct OrderPage {
    document: Document,
    regex: Regex,
}

impl OrderPage {
    pub fn new(html: &str) -> OrderPage {
        OrderPage {
            document: Document::from(html),
            regex: Regex::new(r"'(.{32})', '(\d{18})'").unwrap(),
        }
    }

    pub fn parse(self, comment: bool) -> Self {
        for user in self.document.find(
            Attr("id", "report")
                .descendant(Name("tbody"))
                .descendant(Class("memberTr"))
        ) {
            let name = user.find(Class("_buyerNick"))
                .next()
                .unwrap()
                .attr("_buyernick")
                .unwrap();
            let app_scheme = format!("aliim:sendmsg?touid=cntaobao{}", name);

            #[cfg(windows)]
            {
                Command::new("cmd.exe")
                    .args(&["/C", "start", &app_scheme])
                    .spawn()
                    .unwrap();

                unsafe {
                    use winapi::um::winuser::{
                        VK_HOME,
                        GetAsyncKeyState,
                    };

                    if GetAsyncKeyState(VK_HOME) & 1 != 0 { loop { if GetAsyncKeyState(VK_HOME) & 1 != 0 { break; } } }
                }
            }

            if comment {
                let ids = user.find(Class("visitCommentsInput"))
                    .next()
                    .unwrap()
                    .attr("onblur")
                    .unwrap();
                let caps = self.regex.captures(ids).unwrap();
                let trade_oid = caps.get(1)
                    .unwrap()
                    .as_str();
                let tid = caps.get(2)
                    .unwrap()
                    .as_str();

                VANGUARD.send_comment(&tid, &trade_oid);
                sleep(Duration::from_millis(500));
            }

            let mut count = COUNT.lock().unwrap();
            *count += 1;
            println!("Progress: {}, User: {}", count, name);
        }

        self
    }

    pub fn has_next(&self) -> bool {
        if let Some(_) = self.document
            .find(Attr("class", "next disabled"))
            .next() { false } else { true }
    }
}
