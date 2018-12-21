#[derive(Clone, Debug)]
pub struct Track {
    pub id: u64,
    pub name: String,
    pub playable: bool,
    pub paid: bool,
    pub duration: u64,
    pub src: String,
    pub buy: bool,
    pub like: bool,
    pub copyright: bool,
}

impl Track {
    pub fn from_json(json: &serde_json::Value) -> Track {
        let src = json["src"].as_str().unwrap().to_owned();
        let name = format!("{}.{}", json["trackName"].as_str().unwrap(), src.split('.').last().unwrap());

        Track {
            id: json["trackId"].as_u64().unwrap(),
            name,
            playable: json["canPlay"].as_bool().unwrap(),
            paid: json["isPaid"].as_bool().unwrap(),
            duration: json["duration"].as_u64().unwrap(),
            src,
            buy: json["hasBuy"].as_bool().unwrap(),
            like: json["isLike"].as_bool().unwrap(),
            copyright: json["isCopyright"].as_bool().unwrap(),
        }
    }
}
