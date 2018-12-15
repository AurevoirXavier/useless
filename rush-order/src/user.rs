// --- std ---
use std::{
    fs::File,
    io::{Write, stdin, stdout},
    process::Command,
};

// --- external ---
use reqwest::{
    Client,
    ClientBuilder,
    Response,
    header::{COOKIE, SET_COOKIE, HeaderMap, HeaderValue},
};

pub trait User<U> {
    fn get_captcha(&mut self, retry: bool) -> String;

    fn sign_in(&mut self) -> bool;

    fn order(self);
}

pub fn load_cookie(session: &mut Client, cookie: HeaderValue) {
    *session = {
        let mut headers = HeaderMap::new();
        headers.insert(COOKIE, cookie);
        ClientBuilder::new()
            .danger_accept_invalid_certs(true)
            .danger_accept_invalid_hostnames(true)
            .default_headers(headers)
            .build()
            .unwrap()
    };
}

pub fn save_captcha(mut resp: Response) -> String {
    let mut captcha = vec![];
    resp.copy_to(&mut captcha).unwrap();

    let mut f = File::create("captcha.png").unwrap();
    f.write(&captcha).unwrap();

    Command::new("open")
        .arg("captcha.png")
        .spawn()
        .unwrap();

    print!("User {}, captcha -> ", name);
    stdout().flush().unwrap();

    let mut captcha = String::new();
    stdin().read_line(&mut captcha).unwrap();
    captcha
}
