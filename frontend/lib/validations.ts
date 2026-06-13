import { z } from 'zod'

export const deployFormSchema = z.object({
  name: z.string().min(1),
  initArgs: z.string().optional(),
  cycles: z.number().int().nonnegative(),
  subnet: z.string().optional(),
})

export const canisterFiltersSchema = z.object({
  search: z.string().optional(),
  status: z.enum(['running', 'stopped', 'error', 'deploying', 'failed']).optional(),
  sortBy: z.enum(['name', 'status', 'createdAt', 'cycles', 'lastDeployed']).optional(),
  sortOrder: z.enum(['asc', 'desc']).optional(),
}).partial()
