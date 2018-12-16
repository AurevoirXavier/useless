#[macro_use]
extern crate lazy_static;
extern crate regex;
extern crate reqwest;
extern crate serde_json;

mod user;
mod website;

// --- std ---
use std::io::{Write, stdin, stdout};

// --- custom ---
use self::{
    user::User,
    website::{
        liuyuz::LiuYuZ,
        xinqiyang::XinQiYang,
    },
};

fn main() {
    print!("1. liuyuz.com    2. xinqiyang.cn\n> ");
    stdout().flush().unwrap();

    let mut website = String::new();
    stdin().read_line(&mut website).unwrap();

    match website.trim() {
        "1" => LiuYuZ::rush(),
        "2" => XinQiYang::rush(),
        _ => unreachable!()
    }
}
