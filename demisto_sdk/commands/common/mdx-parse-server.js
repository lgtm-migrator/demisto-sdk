const mdx = require('@mdx-js/mdx');
const http = require('http')
const markdownlint = require('markdownlint')
const markdownlintRuleHelpers = require('markdownlint-rule-helpers')


function markdownLint(req, res, body) {

    res.statusCode = 200

    fileName = "fileName"
    const fixOptions = {
      "strings": {
        fileName : body
      }
    };
    let validationResults = markdownlint.sync(fixOptions);

    let fixedText = null;
    if(req.url.includes('fix')) {
        const fixes = validationResults[fileName].filter(error => error.fixInfo);
        if (fixes.length > 0) {
            fixedText = markdownlintRuleHelpers.applyFixes(body, fixes);
        }
        const fixOptions = {
            "strings": {
            fileName : fixedText
            }
        };
        validationResults = markdownlint.sync(fixOptions)
    }
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ "validations" : validationResults.toString(), fixedText : fixedText}))

}
function requestHandler(req, res) {
    // console.log(req)
    if (req.method != 'POST') {
        res.statusCode = 405
        res.end('Only POST is supported')
    }
    let body = ''
    req.setEncoding('utf8');
    req.on('data', function (data) {
        body += data
    })
    req.on('end', async function () {
        //   console.log('Body length: ' + body.length)
        console.log(req.url)
        if(req.url.includes('/markdownlint'))
        {
            markdownLint(req, res, body)
        }
        else {
            try {
                parsed = await mdx(body)
                res.end('Successfully parsed mdx')
            } catch (error) {
                res.statusCode = 500
                res.end("MDX parse failure: " + error)
            }
        }

    })
}

const server = http.createServer(requestHandler);

server.listen(6161, (err) => {
    if (err) {
        return console.log('MDX server failed starting.', err)
    }
    console.log(`MDX server is listening on port: 6161`)
});
