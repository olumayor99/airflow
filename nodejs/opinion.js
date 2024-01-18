"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const puppeteer_1 = require("puppeteer");
const [, , keyFileArg, certFileArg, passwordArg, rfc] = process.argv;
// Set default values if arguments are not provided
const password = passwordArg;
const keyFile = keyFileArg;
const certFile = certFileArg;
function delay(time) {
    return new Promise(function (resolve) {
        setTimeout(resolve, time);
    });
}
const load_page = async (page) => {
    await page.goto('https://ptsc32d.clouda.sat.gob.mx/?/reporteOpinion32DContribuyente');
    await delay(1300);
    console.log("load page!!!");
};
const login = async (page) => {

    const frame = page.frames()[0];
    page.waitForNavigation({ waitUntil: ['domcontentloaded', 'networkidle2', 'networkidle0'] });
    await delay(8000);
    const certInput = await frame.waitForSelector('#fileCertificate');
    await certInput.uploadFile(certFile);
    const keyInput = await frame.waitForSelector('#filePrivateKey');
    await keyInput.uploadFile(keyFile);
    const passwordInput = await frame.$('#privateKeyPassword');
    await passwordInput.type(password);
    await frame.click('#submit');
    console.log("login!!!");
};
const downloadPDFFromIframe = async (page) => {
    // Wait for the iframe to appear
    page.waitForNavigation({ waitUntil: ['domcontentloaded', 'networkidle2', 'networkidle0'] });
    await page.waitForSelector('iframe');
    console.log("Downloaaaaaad!!!");
    // Evaluate the code inside the iframe's context
    await page.evaluate((rfc) => {
        const pdf_name = `./opinion_${rfc}.pdf`;
        const pdfFrame = document.querySelector("iframe");
        // Get the data URL from the iframe's src attribute
        const pdfDataUrl = pdfFrame.getAttribute('src');
        // Create anpdf_name anchor element within the iframe's document
        const anchor = document.createElement('a');
        // Set the anchor's properties
        anchor.href = pdfDataUrl;
        anchor.download = pdf_name;
        // Append the anchor to the iframe's document
        document.body.appendChild(anchor);
        // Trigger a click event on the anchor to initiate the download
        anchor.click();
        // Clean up by removing the anchor element
        document.body.removeChild(anchor);
    }, rfc);
    console.log("Downloaaaaaad FINIIIIIIIISH!!!");
};
const close = async (page, browser) => {
    await delay(3000);
    await page.close();
    await browser.close();
    console.log("CLOSEEEEE")
};
const run = async () => {
    const browser = await puppeteer_1.default.launch({
        headless: "new",
        args: ['--no-sandbox', '--incognito'],
    });

    // Create a new incognito context with a custom download path
    const context = await browser.createIncognitoBrowserContext();

    const page = await context.newPage();

    // Set up CDP session to customize download behavior
    const client = await page.target().createCDPSession();
    await client.send('Page.setDownloadBehavior', {
        behavior: 'allow',
        downloadPath: '/opt/', // Change this to your desired download path
    });

    await load_page(page);
    await login(page);
    await downloadPDFFromIframe(page);
    await close(page, browser);
};

run();
