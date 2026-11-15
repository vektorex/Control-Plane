const fs = require('fs');
const path = require('path');

const bundlePath = path.join('node_modules', 'next', 'dist', 'compiled', 'webpack', 'bundle5.js');

if (fs.existsSync(bundlePath)) {
  try {
    let content = fs.readFileSync(bundlePath, 'utf-8');
    if (content.includes('const isDir=')) {
      // Already patched safely, do not re-patch or duplicate declarations
      process.exit(0);
    }
    const startStr = 'const mkdirp=(v,I,P)=>';
    const endStr = ';const readJson=';

    const startIdx = content.indexOf(startStr);
    const endIdx = content.indexOf(endStr);

    if (startIdx !== -1 && endIdx !== -1) {
      const newBlock = 'const isDir=(v,p)=>{try{return v.statSync(p).isDirectory()}catch(e){return false}};const mkdirp=(v,I,P)=>{if(isDir(v,I)){P();return}v.mkdir(I,(R=>{if(R){if(R.code==="ENOENT"||R.code==="EPERM"){const $=dirname(v,I);if($===I){P(R);return}mkdirp(v,$,(R=>{if(R){P(R);return}v.mkdir(I,(v2=>{if(v2){if(v2.code==="EEXIST"||v2.code==="EPERM"||isDir(v,I)){P();return}P(v2);return}P()}))}));return}else if(R.code==="EEXIST"||isDir(v,I)){P();return}P(R);return}P()}))};v.exports.mkdirp=mkdirp;const mkdirpSync=(v,I)=>{if(isDir(v,I)){return}try{v.mkdirSync(I)}catch(P){if(P){if(P.code==="ENOENT"||P.code==="EPERM"){const R=dirname(v,I);if(R===I){throw P}mkdirpSync(v,R);try{v.mkdirSync(I)}catch(e2){if(!isDir(v,I)&&e2.code!=="EEXIST"&&e2.code!=="EPERM")throw e2}return}else if(P.code==="EEXIST"||isDir(v,I)){return}throw P}}};v.exports.mkdirpSync=mkdirpSync';
      content = content.substring(0, startIdx) + newBlock + content.substring(endIdx);
      fs.writeFileSync(bundlePath, content, 'utf-8');
      console.log('[scripts/patch_webpack.js] Applied Windows Webpack mkdir resilience patch.');
    }
  } catch (err) {
    console.warn('[scripts/patch_webpack.js] Note: Could not patch webpack bundle:', err.message);
  }
}
