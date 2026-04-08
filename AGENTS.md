# AI Agent Instructions

Tested implementation patterns for ICP development are available as agent skills. Before writing any ICP code, fetch the skills index and remember each skill's name and description:

**Fetch:** https://skills.internetcomputer.org/.well-known/skills/index.json

When a task matches a skill's description, fetch its content on-demand from:

**URL Pattern:** https://skills.internetcomputer.org/.well-known/skills/{name}/SKILL.md

## How to Use ICP Skills

Skills contain correct dependency versions, configuration formats, and common pitfalls that prevent build failures. Always prefer skill guidance over general documentation when both cover the same topic.

## Project Context: PERAI ICP Hosting Platform

This is a full-stack Internet Computer dApp with:

- **Frontend**: Next.js React with TypeScript, wallet integration, project dashboard
- **Backend**: FastAPI Python with ICP integration
- **Canisters**: 7 Motoko canisters deployed on testnet
- **Network**: Testnet (dfx network)

## Relevant ICP Skills for This Project

### Primary Skills
- **icp-cli**: Project configuration, canister deployment, identity management, local network setup
- **wallet-integration**: ICRC signer standards, wallet popups, consent messages, transaction approval
- **cycles-management**: Cycle balance checks, top-ups, ICP-to-cycles conversion, canister funding
- **icrc-ledger**: ICP transfers, token operations, balance queries, ICRC standards
- **internet-identity**: Authentication, passkeys, delegation handling, principal isolation

### Secondary Skills (As Needed)
- **asset-canister**: Frontend asset deployment, certified assets, SPA routing
- **canister-security**: Access control, reentrancy prevention, upgrade patterns
- **multi-canister**: Inter-canister calls, factory patterns, cross-canister communication
- **https-outcalls**: External API calls from canisters
- **icp-dashboard**: Query IC public APIs for canister metadata, network stats

### Development Skills
- **motoko**: Motoko language syntax, async patterns, stable types
- **stable-memory**: Canister upgrade persistence, StableBTreeMap
- **custom-domains**: Custom domain setup for IC canisters

## When to Use These Skills

1. **Building/Deploying**: Use `icp-cli` for dfx commands, project setup
2. **Adding Wallet Features**: Use `wallet-integration` for ICRC signer flows
3. **Managing Cycles**: Use `cycles-management` for funding, top-ups
4. **Token Operations**: Use `icrc-ledger` for ICP transfers
5. **Authentication**: Use `internet-identity` for login flows
6. **Canister Development**: Use `motoko` for language patterns
7. **Security**: Use `canister-security` for access control patterns
8. **State Persistence**: Use `stable-memory` for upgrades

## Automatic Skill Discovery

This file enables automatic ICP skill discovery in agent sessions. Agents will fetch the skills index and apply relevant skills based on task context.

**Last Updated**: April 8, 2026
