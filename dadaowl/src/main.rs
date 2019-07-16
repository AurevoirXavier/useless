#[macro_use]
extern crate lazy_static;
extern crate regex;
extern crate reqwest;
extern crate select;
#[cfg(windows)]
extern crate winapi;

mod order_page;
mod vanguard;

// --- custom ---
use self::vanguard::Vanguard;

fn main() {
    if !Vanguard::auth() {
        println!("Unauthorized user");
        return;
    }

    Vanguard::start();
}
