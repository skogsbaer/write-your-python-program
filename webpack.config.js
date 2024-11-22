const path = require('path');

module.exports = {
  entry: {
    linkerline: './media/programflow-visualization/linkerline.js',
  },
  output: {
    path: path.resolve(__dirname, 'out'),
    filename: '[name].bundle.js',
  },
  mode: "production"
};
