// Loads the JMdict WASM binary for the active dictionary mode and exposes
// window.jmdictReady — a Promise that resolves with a Proxy object that
// supports jmdict[word] bracket access backed by the WASM lookup() function.
(function () {
    var mode = localStorage.getItem('dictionaryMode') === 'ultra' ? 'ultra' : 'full';
    var wasmJs = mode === 'ultra'
        ? './pkg/jmdict_ultra_wasm.js'
        : './pkg/jmdict_full_wasm.js';

    window.jmdictReady = import(wasmJs).then(function (mod) {
        return mod.default().then(function () {
            console.log('[timing] jmdict wasm ready: ' + performance.now().toFixed(0) + ' ms');
            return new Proxy({}, {
                get: function (_, word) {
                    if (typeof word !== 'string') return undefined;
                    var result = mod.lookup(word);
                    return result === null ? undefined : result;
                },
                has: function (_, word) {
                    return mod.lookup(word) !== null;
                }
            });
        });
    });
})();
