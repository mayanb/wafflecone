'use strict';

module.exports = {
    module: {
        loaders: [
            {
                test: /\.jsx?$/,
                loader: 'babel',
                exclude: /node_modules/,
                query: {
                    presets: ['react', 'es2015']
                }
            },
            {
                test: /(\.scss|\.css)$/,
                loaders: ["style", "css?modules", "sass"]
            },
{
    test: /\.json$/,
    loader: "json-loader"
}
        ],
    },
    entry: './src/app.jsx',
    output: {
        filename: './public/app.js'
    }
};