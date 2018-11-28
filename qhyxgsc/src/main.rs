#[macro_use]
extern crate lazy_static;
extern crate reqwest;

// --- std ---
use std::{
    env::args,
    fs::File,
    io::Read,
    time::Duration,
    thread::{self, sleep},
};

// --- external ---
use reqwest::{
    Client,
    ClientBuilder,
    header::{COOKIE, SET_COOKIE, HeaderMap},
};

lazy_static! { static ref WAIT: u64 = args().collect::<Vec<String>>()[1].parse().unwrap(); }

struct Account<'a> {
    username: &'a str,
    password: &'a str,
    session: Client,
}

impl<'a> Account<'a> {
    fn new(username: &'a str, password: &'a str) -> Account<'a> {
        Account {
            username,
            password,
            session: Client::new(),
        }
    }

    fn default_client_builder() -> ClientBuilder {
        ClientBuilder::new()
            .danger_accept_invalid_certs(true)
            .danger_accept_invalid_hostnames(true)
            .gzip(true)
    }

    fn load_cookie(&mut self, headers: &HeaderMap) {
        let headers = {
            let cookie = headers.get(SET_COOKIE).unwrap().to_owned();
            let mut headers = HeaderMap::new();
            headers.insert(COOKIE, cookie);
            headers
        };

        self.session = Account::default_client_builder()
            .default_headers(headers)
            .build()
            .unwrap();
    }

    fn sign_in(mut self) -> Self {
        let resp = Account::default_client_builder()
            .build()
            .unwrap()
            .post("http://www.qhyxgsc.cn/index.php/index/login/index.html")
            .form(&[("username", self.username), ("pwd", self.password)])
            .send()
            .unwrap();

        self.load_cookie(resp.headers());

        println!("账号 [{}] 登陆成功。", self.username);

        self
    }

    fn make_money(&self) {
        self.session.get("http://www.qhyxgsc.cn/index.php/index/index/time.html");

        for ad_id in 1u32.. {
            println!("账号 [{}] 正在点击第 [{}] 个广告。", self.username, ad_id);

            self.session
                .post("http://www.qhyxgsc.cn/index.php/index/index/guanggao.html")
                .form(&[("id", ad_id)])
                .send()
                .unwrap();

            if self.session
                .get("http://www.qhyxgsc.cn/index.php/index/index/hdmoney.html")
                .send()
                .unwrap()
                .text()
                .unwrap()
                .trim() == "1" {
                println!("账号 [{}] 到达上限。", self.username);
                return;
            }

            sleep(Duration::from_secs(WAIT.clone()));
        }
    }
}

fn dispatch() {
    let accounts = {
        let mut accounts = String::new();
        let mut f = File::open("accounts.txt").unwrap();
        f.read_to_string(&mut accounts).unwrap();

        accounts
    };

    let mut handles = vec![];
    for account in accounts.lines() {
        let account: Vec<&str> = account.split('=').collect();
        let username = account[0].to_owned();
        let password = account[1].to_owned();

        let handle = thread::spawn(move || {
            let account = Account::new(&username, &password);
            account.sign_in().make_money();
        });

        handles.push(handle);
    }

    for handle in handles { handle.join().unwrap(); }
}

fn main() { dispatch(); }
