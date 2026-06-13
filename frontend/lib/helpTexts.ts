export function getHelpText(key: string) {
  const texts: Record<string, string> = {
    subnet: 'Choose a subnet or leave blank to auto-select the best one.',
    cycles: 'Initial cycles are used for deployment and hosting costs.',
    initArgs: 'Optional candid initialization arguments for your canister.',
  }

  return texts[key] || ''
}
