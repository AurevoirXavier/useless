#[macro_use]
extern crate conrod;
#[macro_use]
extern crate lazy_static;
extern crate reqwest;
extern crate serde_json;

mod fetcher;
mod ui;

fn main() { ui::display(); }
