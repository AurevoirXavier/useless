// --- external ---
use reqwest::Client;

// --- custom ---
use crate::user::User;

pub struct LiuYuZ {
    name: String,
    session: Client,
}

impl User<LiuYuZ> for LiuYuZ {
    fn sign_in(&mut self) -> bool {
        unimplemented!()
    }

    fn order(self) {
        unimplemented!()
    }
}

impl LiuYuZ {
    fn sign_in() {}
}
