'use strict';

module.exports = {
    resolve: {
        extensions: ['', '.jsx', '.js', '.json', '.scss'],
        modules: ['node_modules']
    },
    module: {
        loaders: [ {
            test: /\.jsx?$/,
            loader: 'babel-loader',
            exclude: /node_modules/,
            query: {
                presets: ['react', 'env'],
                plugins: ["transform-object-rest-spread"]
            }
        }, {
            test: /(\.scss|\.css)$/,
            include: /(src|react-toolbox)/,
            loaders: [
                require.resolve('style-loader'),
                require.resolve('css-loader') + '?sourceMap&modules&importLoaders=1&localIdentName=[name]__[local]___[hash:base64:5]',
                 require.resolve('sass-loader') + '?sourceMap'
            ]
        }, {
            test: /\.json$/,
            loader: "json-loader"
        }, {
            test: /\.js$/,
            loader: require.resolve('babel-loader'),
            exclude: /node_modules/,
        } ],
    },
    entry: './src/components/app.jsx',
    output: {
        filename: './public/app.js'
    },
};