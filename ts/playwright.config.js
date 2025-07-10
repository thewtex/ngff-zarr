// @ts-check

/**
 * @see https://playwright.dev/docs/test-configuration
 */
const config = {
  testDir: "./test/browser-npm",
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: false,
  /* Retry on CI only */
  retries: 0,
  /* Opt out of parallel tests on CI. */
  workers: 1,
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: "list",
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: "http://localhost:3000",
    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: "on-first-retry",
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: "chromium",
      use: {
        channel: "chrome",
      },
    },

    {
      name: "firefox",
      use: {
        browserName: "firefox",
      },
    },

    {
      name: "webkit",
      use: {
        browserName: "webkit",
      },
    },

    /* Test against mobile viewports. */
    {
      name: "Mobile Chrome",
      use: {
        browserName: "chromium",
        isMobile: true,
        viewport: { width: 393, height: 851 },
      },
    },
    {
      name: "Mobile Safari",
      use: {
        browserName: "webkit",
        isMobile: true,
        viewport: { width: 375, height: 667 },
      },
    },

    /* Test against branded browsers. */
    {
      name: "Microsoft Edge",
      use: {
        channel: "msedge",
      },
    },
    {
      name: "Google Chrome",
      use: {
        channel: "chrome",
      },
    },
  ],

  /* Run your local dev server before starting the tests */
  webServer: {
    command: "deno task dev:server",
    url: "http://localhost:3000",
    reuseExistingServer: true,
  },
};

export default config;
