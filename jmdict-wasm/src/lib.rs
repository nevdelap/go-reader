use std::cmp::Ordering;

use serde::{Deserialize, Serialize};
use wasm_bindgen::prelude::*;

static DATA: &[u8] = include_bytes!(concat!(env!("OUT_DIR"), "/jmdict.bin"));

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

// Binary format (all integers little-endian):
//   Bytes  0- 3: b"JMDI" magic
//   Bytes  4- 7: num_entries (u32)
//   Bytes  8-11: key_pool_start (u32)
//   Bytes 12-15: entry_pool_start (u32)
//   Bytes 16..(16 + num_entries*14): Index table sorted by key bytes
//     Each 14-byte record: key_start(u32) key_len(u16) entry_start(u32) entry_len(u32)
//   key_pool: all key strings concatenated
//   entry_pool: all entries postcard-serialized, concatenated

#[wasm_bindgen]
pub fn lookup(word: &str) -> JsValue {
    let num_entries = u32::from_le_bytes(DATA[4..8].try_into().unwrap()) as usize;
    let key_pool_start = u32::from_le_bytes(DATA[8..12].try_into().unwrap()) as usize;
    let entry_pool_start = u32::from_le_bytes(DATA[12..16].try_into().unwrap()) as usize;

    let index = &DATA[16..key_pool_start];
    let key_pool = &DATA[key_pool_start..entry_pool_start];
    let entry_pool = &DATA[entry_pool_start..];

    let word_bytes = word.as_bytes();

    let mut lo = 0usize;
    let mut hi = num_entries;
    while lo < hi {
        let mid = lo + (hi - lo) / 2;
        let b = mid * 14;
        let key_start = u32::from_le_bytes(index[b..b + 4].try_into().unwrap()) as usize;
        let key_len = u16::from_le_bytes(index[b + 4..b + 6].try_into().unwrap()) as usize;
        let key = &key_pool[key_start..key_start + key_len];

        match key.cmp(word_bytes) {
            Ordering::Equal => {
                let entry_start =
                    u32::from_le_bytes(index[b + 6..b + 10].try_into().unwrap()) as usize;
                let entry_len =
                    u32::from_le_bytes(index[b + 10..b + 14].try_into().unwrap()) as usize;
                let entry: Entry =
                    postcard::from_bytes(&entry_pool[entry_start..entry_start + entry_len])
                        .expect("postcard deserialize failed");
                return entry_to_js(&entry);
            }
            Ordering::Less => lo = mid + 1,
            Ordering::Greater => hi = mid,
        }
    }
    JsValue::NULL
}

fn entry_to_js(entry: &Entry) -> JsValue {
    let obj = js_sys::Object::new();
    set(&obj, "p", &str_array(&entry.p));
    set(&obj, "g", &str_array_array(&entry.g));
    if !entry.pg.is_empty() {
        set(&obj, "pg", &str_array(&entry.pg));
    }
    if !entry.pg2.is_empty() {
        set(&obj, "pg2", &str_array(&entry.pg2));
    }
    obj.into()
}

fn set(obj: &js_sys::Object, key: &str, val: &JsValue) {
    js_sys::Reflect::set(obj, &JsValue::from_str(key), val).unwrap();
}

fn str_array(v: &[String]) -> JsValue {
    let arr = js_sys::Array::new();
    for s in v {
        arr.push(&JsValue::from_str(s));
    }
    arr.into()
}

fn str_array_array(v: &[Vec<String>]) -> JsValue {
    let arr = js_sys::Array::new();
    for inner in v {
        arr.push(&str_array(inner));
    }
    arr.into()
}
