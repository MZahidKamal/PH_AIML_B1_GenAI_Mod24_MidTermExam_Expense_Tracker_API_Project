// Allure 3 configuration (read automatically by the Allure CLI)
import {defineConfig} from "allure";

export default defineConfig({
    // Title shown at the top of the report
    name: "Expense Tracker API - Test Report",

    // Where the generated report is written
    output: "./tests/reports/allure-report",

    plugins: {
        // "Awesome" is Allure 3's modern UI
        awesome: {
            options: {
                // One standalone HTML file: easy to share (email, Slack, CI artifact) and opens without a web server
                singleFile: true,
                reportLanguage: "en",
                // Tree on the left: Epic (Auth / Transactions / ...) -> Feature (Register / Filter / ...) -> tests
                groupBy: ["epic", "feature"],
            },
        },
    },
});
