use js_sys::Function;
use serde::Serialize;
use wasm_bindgen::prelude::*;

const IDX_POS: usize = 0;
const IDX_POS_DETAIL_1: usize = 1;
const IDX_BASIC_FORM: usize = 6;
const IDX_READING: usize = 7;

#[derive(Serialize, Clone)]
pub struct Token {
    pub surface_form: String,
    pub reading: String,
    pub basic_form: String,
    pub pos: String,
    pub pos_detail_1: String,
}

#[cfg(not(target_arch = "wasm32"))]
pub fn tokenize_native(text: &str) -> Vec<Token> {
    let tokenizer = build_tokenizer().expect("failed to build tokenizer");
    let mut tokens = tokenizer.tokenize(text).expect("tokenize failed");
    tokens
        .iter_mut()
        .map(|t| {
            let surface_form = t.text.to_string();
            let d = t.get_details().unwrap_or_default();
            Token {
                surface_form,
                reading: d.get(IDX_READING).unwrap_or(&"*").to_string(),
                basic_form: d.get(IDX_BASIC_FORM).unwrap_or(&"*").to_string(),
                pos: d.get(IDX_POS).unwrap_or(&"*").to_string(),
                pos_detail_1: d.get(IDX_POS_DETAIL_1).unwrap_or(&"*").to_string(),
            }
        })
        .collect()
}

#[wasm_bindgen]
pub struct JsTokenizer {
    inner: lindera_tokenizer::tokenizer::Tokenizer,
}

#[wasm_bindgen]
impl JsTokenizer {
    pub fn tokenize(&mut self, text: &str) -> Result<JsValue, JsValue> {
        let mut tokens = self
            .inner
            .tokenize(text)
            .map_err(|e| JsValue::from_str(&e.to_string()))?;

        let out: Vec<Token> = tokens
            .iter_mut()
            .map(|t| {
                let surface_form = t.text.to_string();
                let d = t.get_details().unwrap_or_default();
                Token {
                    surface_form,
                    reading: d.get(IDX_READING).unwrap_or(&"*").to_string(),
                    basic_form: d.get(IDX_BASIC_FORM).unwrap_or(&"*").to_string(),
                    pos: d.get(IDX_POS).unwrap_or(&"*").to_string(),
                    pos_detail_1: d.get(IDX_POS_DETAIL_1).unwrap_or(&"*").to_string(),
                }
            })
            .collect();

        serde_wasm_bindgen::to_value(&out).map_err(|e| JsValue::from_str(&e.to_string()))
    }
}

#[wasm_bindgen]
pub fn builder(_opts: JsValue) -> Builder {
    Builder
}

#[wasm_bindgen]
pub struct Builder;

#[wasm_bindgen]
impl Builder {
    pub fn build(&self, callback: &Function) -> Result<(), JsValue> {
        match build_tokenizer() {
            Ok(inner) => {
                let tok = JsTokenizer { inner };
                let js_tok = JsValue::from(tok);
                callback.call2(&JsValue::NULL, &JsValue::NULL, &js_tok)?;
            }
            Err(e) => {
                let err = JsValue::from_str(&e.to_string());
                callback.call2(&JsValue::NULL, &err, &JsValue::UNDEFINED)?;
            }
        }
        Ok(())
    }
}

fn build_tokenizer(
) -> Result<lindera_tokenizer::tokenizer::Tokenizer, Box<dyn std::error::Error>> {
    use lindera_core::mode::Mode;
    use lindera_dictionary::{DictionaryConfig, DictionaryKind};
    use lindera_tokenizer::tokenizer::{Tokenizer, TokenizerConfig};

    let config = TokenizerConfig {
        dictionary: DictionaryConfig {
            kind: Some(DictionaryKind::IPADIC),
            path: None,
        },
        user_dictionary: None,
        mode: Mode::Normal,
    };
    Ok(Tokenizer::from_config(config)?)
}
