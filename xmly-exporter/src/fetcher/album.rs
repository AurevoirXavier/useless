// --- custom ---
use super::{
    FETCHER,
    track::Track,
};

const ALBUM_URL: &'static str = "https://www.ximalaya.com/revision/play/album?albumId=";

#[derive(Clone, Debug)]
pub struct Album {
    url: String,
    name: String,
    tracks: Vec<Track>,
}

impl Album {
    pub fn new() -> Album {
        Album {
            url: String::new(),
            name: String::new(),
            tracks: vec![],
        }
    }

    pub fn set_id(&mut self, id: &str) -> &mut Self {
        self.url = format!("{}{}", ALBUM_URL, id);
        self
    }

    fn get_album_name(&mut self) -> String {
        let resp: serde_json::Value = FETCHER.get(&format!("{}&pageNum=1&pageSize=1", self.url))
            .json()
            .unwrap();

        resp["data"]["tracksAudioPlay"]
            .as_array()
            .unwrap()[0]["albumName"]
            .as_str()
            .unwrap()
            .to_owned()
    }

    pub fn fetch(&mut self) -> &mut Self {
        self.tracks.clear();

        let fetcher = FETCHER.clone();
        for page_num in 1u8.. {
            if let Ok(resp) = fetcher.get(&format!("{}&pageNum={}", self.url, page_num)).json::<serde_json::Value>() {
                let data = &resp["data"];

                {
                    let tracks = data["tracksAudioPlay"].as_array().unwrap();
                    if tracks.is_empty() { return self; }
                    for track in tracks { self.tracks.push(Track::from_json(track)); }
                }

                if !data["hasMore"].as_bool().unwrap() {
                    self.name = self.get_album_name();
                    return self;
                }
            } else { return self; }
        }

        self
    }

    pub fn tracks_detail(&self) -> Vec<String> {
        let mut detail = vec![];

        for track in self.tracks.iter() {
            let (minutes, seconds) = {
                let duration = track.duration;
                (duration / 60, duration % 60)
            };

            detail.push(format!("{}    {}:{:0>2}", track.name, minutes, seconds));
        }

        detail
    }

    pub fn save_aria2_input_file(&self) -> &Self {
        // --- std ---
        use std::fs::write;

        let mut tracks = String::new();
        for track in self.tracks.iter() {
            tracks.push_str(&format!("{}\n\tout={}\n\tdir={}\n", track.src, track.name, self.name));
        }

        write(&format!("{}.ax", self.name), tracks).unwrap();

        self
    }
}
