extern crate reqwest;

// --- external ---
use reqwest::Client;

struct Session(Client);

impl Session {
    fn new() -> Session { Session(Client::new()) }

    fn get_text(&self, url: &str) -> String {
        loop {
            if let Ok(mut resp) = self.0.get(url).send() {
                if let Some(resp) = resp.text() { return resp; }
            }
        }
    }

    fn post_text(&self)
}

struct User(Session);

impl User {
    fn sign_in(username: &str, password: &str) -> User {
        unimplemented!()
    }
}

fn main() {
    println!("Hello, world!");
}
