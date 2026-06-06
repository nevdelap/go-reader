use std::collections::HashMap;
use std::env;
use std::fs::{self, File};
use std::path::Path;

use flate2::read::GzDecoder;
use serde::{Deserialize, Serialize};

#[derive(Deserialize, Serialize)]
struct Entry {
    #[serde(default)]
    p: Vec<String>,
    g: Vec<Vec<String>>,
    #[serde(default)]
    pg: Vec<String>,
    #[serde(default)]
    pg2: Vec<String>,
}

fn main() {
    #[cfg(feature = "full")]
    let filename = "dict/jmdict-full.json.gz";
    #[cfg(not(feature = "full"))]
    let filename = "dict/jmdict-ultra-compact.json.gz";

    let repo_root = Path::new(env!("CARGO_MANIFEST_DIR")).parent().unwrap();
    let dict_path = repo_root.join(filename);

    println!("cargo:rerun-if-changed={}", dict_path.display());

    let file = File::open(&dict_path)
        .unwrap_or_else(|_| panic!("Cannot open {}", dict_path.display()));
    let reader = GzDecoder::new(file);
    let map: HashMap<String, Entry> = serde_json::from_reader(reader)
        .expect("Failed to parse JMdict JSON");

    // Sort entries by key bytes (UTF-8 byte order == Unicode code point order).
    let mut entries: Vec<(String, Entry)> = map.into_iter().collect();
    entries.sort_unstable_by(|(a, _), (b, _)| a.as_bytes().cmp(b.as_bytes()));

    let mut index_buf = Vec::with_capacity(entries.len() * 14);
    let mut key_pool: Vec<u8> = Vec::new();
    let mut entry_pool: Vec<u8> = Vec::new();

    for (key, entry) in &entries {
        let key_bytes = key.as_bytes();
        let key_start = key_pool.len() as u32;
        let key_len = key_bytes.len() as u16;
        key_pool.extend_from_slice(key_bytes);

        let entry_start = entry_pool.len() as u32;
        let entry_bytes = postcard::to_allocvec(entry).expect("postcard serialize failed");
        let entry_len = entry_bytes.len() as u32;
        entry_pool.extend_from_slice(&entry_bytes);

        // Index record: key_start(u32) + key_len(u16) + entry_start(u32) + entry_len(u32) = 14 bytes
        index_buf.extend_from_slice(&key_start.to_le_bytes());
        index_buf.extend_from_slice(&key_len.to_le_bytes());
        index_buf.extend_from_slice(&entry_start.to_le_bytes());
        index_buf.extend_from_slice(&entry_len.to_le_bytes());
    }

    let num_entries = entries.len() as u32;
    // Header: magic(4) + num_entries(4) + key_pool_start(4) + entry_pool_start(4) = 16 bytes
    let key_pool_start: u32 = 16 + index_buf.len() as u32;
    let entry_pool_start: u32 = key_pool_start + key_pool.len() as u32;

    let mut out = Vec::new();
    out.extend_from_slice(b"JMDI");
    out.extend_from_slice(&num_entries.to_le_bytes());
    out.extend_from_slice(&key_pool_start.to_le_bytes());
    out.extend_from_slice(&entry_pool_start.to_le_bytes());
    out.extend_from_slice(&index_buf);
    out.extend_from_slice(&key_pool);
    out.extend_from_slice(&entry_pool);

    let out_dir = env::var("OUT_DIR").unwrap();
    fs::write(Path::new(&out_dir).join("jmdict.bin"), &out)
        .expect("Failed to write jmdict.bin");
}
