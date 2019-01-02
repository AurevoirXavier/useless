// --- std ---
use std::sync::Arc;
// --- external ---
use reqwest::{
    Client,
    Response,
    header::{COOKIE, HeaderMap},
};

lazy_static! { pub static ref VANGUARD: Arc<Vanguard> = Arc::new(Vanguard::new(&read_line("Cookie -> "))); }

pub struct Vanguard(Client);

impl Vanguard {
    pub fn new(cookie: &str) -> Vanguard {
        // --- std ---
        use std::time::Duration;
        // --- external ---
        use reqwest::ClientBuilder;

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

    pub fn fetch_order_page(&self, page: u32) -> String {
        self.get(&format!("https://trade.1688.com/order/seller_order_list.htm?page={}&trade_status=waitbuyerpay#waitbuyerpay", page))
            .text()
            .unwrap()
            .trim()
            .to_owned()
    }

    pub fn auth() -> bool {
        // --- std ---
        use std::thread;
        // --- external ---
        use select::{
            document::Document,
            predicate::Class,
        };

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

        let user = read_line("User -> ");

        if user.is_empty() { false } else {
            auth_list.join()
                .unwrap()
                .contains(&user)
        }
    }

    pub fn start() {
        // --- custom ---
        use super::order_page::OrderPage;

        let from: u32 = read_line("From -> ").parse().unwrap();
        let to: u32 = read_line("To -> ").parse().unwrap();

        for page in from..=to {
            let html = VANGUARD.fetch_order_page(page);
            let order_page = OrderPage::new(&html);

            if !order_page.parse().has_next() { break; }
        }
    }
}

fn read_line(tips: &str) -> String {
    // --- std ---
    use std::io::{Write, stdin, stdout};

    let mut s = String::new();

    print!("{}", tips);
    stdout().flush().unwrap();
    stdin().read_line(&mut s).unwrap();

    s.trim().to_owned()
}
