// --- std ---
use std::sync::Mutex;
// --- external ---
use select::document::Document;

lazy_static! { static ref COUNT: Mutex<u32> = Mutex::new(0); }

pub struct OrderPage(Document);

impl OrderPage {
    pub fn new(html: &str) -> OrderPage { OrderPage(Document::from(html)) }

    pub fn parse(self) -> Self {
        // --- std ---
        use std::{
            process::Command,
            thread::sleep,
            time::Duration,
        };
        // --- external ---
        use select::predicate::{Attr, Name, Predicate};

        for user in self.0.find(Attr("id", "bd").descendant(Name("li"))) {
            let name = user.find(Attr("class", "fd-left bannerMember"))
                .next()
                .unwrap()
                .attr("data-copytitle")
                .unwrap();
            let app_scheme = format!("aliim:sendmsg?touid=cnalichn{}", name);

            Command::new("cmd.exe")
                .args(&["/C", "start", &app_scheme])
                .spawn()
                .unwrap();

            let mut count = COUNT.lock().unwrap();
            *count += 1;
            println!("Progress: {}, User: {}", count, name);

            sleep(Duration::from_millis(100));
        }

        self
    }

    pub fn has_next(&self) -> bool {
        // --- external ---
        use select::predicate::Attr;

        if let Some(_) = self.0
            .find(Attr("class", "next_none1 button lang-button next"))
            .next() { false } else { true }
    }
}
