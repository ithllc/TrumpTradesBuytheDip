# Robinhood trading integration gate

**Status:** no Robinhood account connection or live order placement is enabled in the public hackathon app. The event requires fictional sample data. A sample filing ticker must never become a live order target.

Robinhood's [third-party connection guidance](https://robinhood.com/us/en/support/articles/third-party-connections/) says trading API access to a customer's account requires written authorization. Robinhood also offers an [Agentic Trading MCP](https://robinhood.com/us/en/support/articles/onboarding-an-external-agent/) for a dedicated user account and supported external agent platforms. The MCP onboarding instructions do not establish that this multi-user public web app is approved to receive brokerage account data or place orders for visitors.

Before implementing a live connection, obtain Robinhood's written approval for this web-app use case or an approved partner integration, its authentication/client details, a test account, and permission to store per-user credentials. Then build a separate authenticated user area with a per-user consent flow, server-side token storage, a visible account disconnect action, order preview, explicit user confirmation for every order, order-status reconciliation, and an audit trail. Keep research/filing evidence distinct from any order recommendation. No Robinhood password should be entered into this app.

The current app has none of those external authorizations or account infrastructure. It should continue to show only the source-grounded, fictional watch event on Render until an approved integration is available and tested.
