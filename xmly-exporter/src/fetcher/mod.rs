pub mod album;
mod track;

// --- std ---
use std::sync::Arc;

// --- external ---
use reqwest::{Client, Response};

struct Fetcher(Client);

impl Fetcher {
    fn new(client: Client) -> Fetcher { Fetcher(client) }

    fn get(&self, url: &str) -> Response {
        loop {
            match self.0.get(url).send() {
                Ok(resp) => return resp,
                Err(_) => continue,
            }
        }
    }
}

lazy_static! {
    static ref FETCHER: Arc<Fetcher> = {
        let mut header = reqwest::header::HeaderMap::new();
        header.insert(reqwest::header::USER_AGENT, "Mozilla/5.0".parse().unwrap());

        Arc::new(Fetcher::new(
            reqwest::ClientBuilder::new()
                .danger_accept_invalid_certs(false)
                .danger_accept_invalid_hostnames(false)
                .default_headers(header)
                .build()
                .unwrap()
        ))
    };
}
