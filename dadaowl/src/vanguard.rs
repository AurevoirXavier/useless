// --- std ---
use std::{
    io::{Write, stdin, stdout},
    sync::Arc,
    thread,
    time::Duration,
};

// --- external ---
use reqwest::{
    Client,
    ClientBuilder,
    Response,
    header::{COOKIE, HeaderMap},
};
use select::{
    document::Document,
    predicate::Class,
};

// --- custom ---
use super::order_page::OrderPage;

lazy_static! {
    pub static ref VANGUARD: Arc<Vanguard> = {
        let mut cookie = String::new();

        print!("Cookie -> ");
        stdout().flush().unwrap();
        stdin().read_line(&mut cookie).unwrap();

        Arc::new(Vanguard::new(cookie.trim()))
    };

    static ref COMMENT: String = {
        let mut comment = String::new();

        print!("Comment -> ");
        stdout().flush().unwrap();
        stdin().read_line(&mut comment).unwrap();

        comment.trim().to_owned()
    };
}

pub struct Vanguard(Client);

impl Vanguard {
    pub fn new(cookie: &str) -> Vanguard {
        let header = {
            let mut header = HeaderMap::new();
            header.insert(COOKIE, cookie.parse().unwrap());

            header
        };

        Vanguard(ClientBuilder::new()
            .danger_accept_invalid_certs(false)
            .danger_accept_invalid_hostnames(false)
            .default_headers(header)
            .timeout(Duration::from_secs(1))
            .build()
            .unwrap())
    }

    fn get(&self, url: &str) -> Response {
        loop {
            match self.0
                .get(url)
                .send() {
                Ok(resp) => return resp,
                Err(_) => continue,
            }
        }
    }

    fn post(&self, url: &str, form: &[(&str, &str)]) -> Response {
        loop {
            match self.0
                .post(url)
                .form(form)
                .send() {
                Ok(resp) => return resp,
                Err(_) => continue,
            }
        }
    }

    pub fn fetch_order_page(&self, page: u32) -> String {
        loop {
            let html = self.get(&format!(
                "http://pingfen.dadaowl.cn/dsr/tbReturnVisit!listDsrBuyerUnrated.action?pageSize=200&pageNo={}&returnVisitSearchParam.sellerRated=false",
                page
            )).text()
                .unwrap()
                .trim()
                .to_owned();

            if html.starts_with("<!DOCTYPE") { return html; }
        }
    }

    pub fn send_comment(&self, tid: &str, trade_oid: &str) {
        loop {
            let resp = self.post(
                "http://pingfen.dadaowl.cn/dsr/$%7BpageContext.request.contextPath%7D/dsr/tbReturnVisit!saveVisitComments.action",
                &[
                    ("returnVisitVo.visitTypeCode", "1"),
                    ("returnVisitVo.tid", tid),
                    ("returnVisitVo.tradeOid", trade_oid),
                    ("returnVisitVo.visitComments", &COMMENT),
                ],
            ).text().unwrap();

            if resp == "success" { return; }

            thread::sleep(Duration::from_millis(500));
        }
    }

    pub fn auth() -> bool {
        let auth_list = thread::spawn(|| {
            let resp = reqwest::get("https://uvwvu.xyz/Rust/auth.rs")
                .unwrap()
                .text()
                .unwrap();
            let document = Document::from(resp.as_str());

            document
                .find(Class("pageContent"))
                .next()
                .unwrap()
                .text()
                .trim()
                .lines()
                .collect::<String>()
        });

        let user = {
            let mut user = String::new();

            print!("User -> ");
            stdout().flush().unwrap();
            stdin().read_line(&mut user).unwrap();

            user.trim().to_owned()
        };

        if user.is_empty() { false } else {
            auth_list.join()
                .unwrap()
                .contains(&user)
        }
    }

    pub fn start() {
        let page_amount: u32 = {
            let mut user = String::new();

            print!("Page -> ");
            stdout().flush().unwrap();
            stdin().read_line(&mut user).unwrap();

            user.trim().parse().unwrap()
        };

        let comment = !COMMENT.is_empty();
        for page in 1..=page_amount {
            let html = VANGUARD.fetch_order_page(page);
            let order_page = OrderPage::new(&html);

            if !order_page.parse(comment).has_next() { break; }
        }
    }
}
