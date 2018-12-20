// --- std ---
use std::{
    process::Command,
    sync::Mutex,
    thread,
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

    pub fn parse(self) -> Self {
        let vanguard = VANGUARD.clone();

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

            let (trade_oid, tid) = {
                let ids = user.find(Class("visitCommentsInput"))
                    .next()
                    .unwrap()
                    .attr("onblur")
                    .unwrap();
                let caps = self.regex.captures(ids).unwrap();

                (
                    caps.get(1)
                        .unwrap()
                        .as_str(),
                    caps.get(2)
                        .unwrap()
                        .as_str()
                )
            };

            Command::new("cmd.exe")
                .args(&["/C", "start", &app_scheme])
                .spawn()
                .unwrap();

            vanguard.send_comment(&tid, &trade_oid);
            thread::sleep(Duration::from_millis(100));

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

#[test]
fn test_parse_has_next() {
    use super::Vanguard;

    let vanguard = Vanguard::new("SERVERID=ec293173e36e8a9aefcf5670980749e2|1545291158|1545287070; JSESSIONID=F2CBB59B2D1450B695A14AEFB75BEA2C; _ati=557235074828");
    let order_page = OrderPage::new(&vanguard.fetch_order_page(17));

    println!("{}", order_page.parse().has_next());
}
