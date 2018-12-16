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
    header::HeaderMap,
};

pub trait User: {
    fn get_captcha(&mut self, retry: bool) -> String;

    fn load_header(session: &mut Client, header: HeaderMap) {
        *session = ClientBuilder::new()
            .danger_accept_invalid_certs(true)
            .danger_accept_invalid_hostnames(true)
            .default_headers(header)
            .build()
            .unwrap();
    }

    fn save_read_captcha(username: &str, mut resp: Response) -> String {
        let mut captcha = vec![];
        resp.copy_to(&mut captcha).unwrap();

        let mut f = File::create("captcha.png").unwrap();
        f.write(&captcha).unwrap();

        Command::new("open")
            .arg("captcha.png")
            .spawn()
            .unwrap();

        print!("User {}, captcha -> ", username);
        stdout().flush().unwrap();

        let mut captcha = String::new();
        stdin().read_line(&mut captcha).unwrap();
        captcha
    }

    fn sign_in(&mut self) -> bool;

    fn load_users() -> Option<Vec<Self>> where Self: Sized;

    fn order(self);

    fn rush();
}
