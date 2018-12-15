#[macro_use]
extern crate lazy_static;
extern crate regex;
extern crate reqwest;

// --- std ---
use std::{
    fs::File,
    io::Read,
    thread,
};

mod user;
mod website;

fn main() {
//    let mut users = vec![];
//
//    let accounts = {
//        let mut accounts = String::new();
//        File::open("accounts.txt")
//            .unwrap()
//            .read_to_string(&mut accounts)
//            .unwrap();
//
//        accounts
//    };
//    for account in accounts.lines() {
//        let mut user = xinqiyang::User::new(account.to_owned());
//        if !user.sign_in() { return; };
//        users.push(user);
//    }
//
//    let mut handlers = vec![];
//    for user in users {
//        let handler = thread::spawn(move || user.rush());
//
//        handlers.push(handler);
//    }
//
//    for handler in handlers { handler.join().unwrap(); }
}
