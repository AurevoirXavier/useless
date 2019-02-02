extern crate reqwest;
extern crate serde_json;
extern crate select;

// --- external ---
use serde_json::Value;
use reqwest::{
    Client,
    header::HeaderMap,
};

fn default_client(headers: HeaderMap) -> Client {
    // --- std ---
    use std::time::Duration;
    // --- external ---
    use reqwest::ClientBuilder;

    ClientBuilder::new()
        .danger_accept_invalid_certs(true)
        .danger_accept_invalid_hostnames(true)
        .default_headers(headers)
        .gzip(true)
        .timeout(Duration::from_secs(3))
        .build()
        .unwrap()
}

struct Kktix(Client);

impl Kktix {
    fn from_cookie(cookie: &str) -> Kktix {
        let mut headers = HeaderMap::new();
        headers.insert(COOKIE, cookie.parse().unwrap());

        Kktix(default_client(headers))
    }

    fn get_register_info(&self) -> Value {
        unimplemented!()
    }
}

fn main() {
    // --- std ---
    use std::io::{Write, stdin, stdout};

    let cookie = {
        print!("Cookie: ");
        stdout().flush().unwrap();
        let mut s = String::new();
        stdin().read_line(&mut s).unwrap();

        s.trim().to_owned()
    };

    let user = Kktix::from_cookie(&cookie);
}
