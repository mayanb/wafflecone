'use strict';

module.exports = {
    module: {
        loaders: [
            {
                test: /\.jsx?$/,
                loader: 'babel-loader',
                exclude: /node_modules/,
                query: {
                    presets: ['react', 'env'],
                    plugins: ["transform-object-rest-spread"]
                }
            },
            {
                test: /(\.scss|\.css)$/,
                loaders: [
                "style-loader", 
                {
                    loader: "css-loader",
                    options: {
                      modules: true,
                      sourceMap: true,
                      importLoaders: 1,
                      localIdentName: "[name]--[local]--[hash:base64:8]"
                    }
                },
                "sass-loader"
                ]
            },
{
    test: /\.json$/,
    loader: "json-loader"
}
        ],
    },
    entry: './src/components/app.jsx',
    output: {
        filename: './public/app.js'
    }
};