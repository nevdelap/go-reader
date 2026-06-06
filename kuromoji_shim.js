// Drop-in replacement for kuromoji.js.
// window.kuromoji is defined synchronously so the app can call builder().build()
// during parse. Callbacks are queued and flushed once WASM is initialized.
(function () {
    const queue = [];
    let wasmBuilder = null;
    let initError = null;

    window.kuromoji = {
        builder(opts) {
            return {
                build(callback) {
                    if (initError) {
                        callback(initError, null);
                    } else if (wasmBuilder) {
                        try { wasmBuilder(opts).build(callback); }
                        catch (e) { callback(e, null); }
                    } else {
                        queue.push({ opts, callback });
                    }
                }
            };
        }
    };

    import('./pkg/kuromoji_wasm.js').then(function (mod) {
        return mod.default().then(function () {
            wasmBuilder = mod.builder;
            for (const item of queue) {
                try { wasmBuilder(item.opts).build(item.callback); }
                catch (e) { item.callback(e, null); }
            }
            queue.length = 0;
        });
    }).catch(function (e) {
        initError = e;
        for (const item of queue) {
            item.callback(e, null);
        }
        queue.length = 0;
    });
})();
