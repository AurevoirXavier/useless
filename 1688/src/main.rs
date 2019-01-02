#[macro_use]
extern crate lazy_static;
extern crate reqwest;
extern crate select;

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
