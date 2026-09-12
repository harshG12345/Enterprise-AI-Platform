import { z } from 'zod';

export const projectCreateSchema = z.object({
  name: z.string().min(2, 'Project name must be at least 2 characters').max(100, 'Project name too long'),
  description: z.string().max(1000, 'Description too long').optional(),
});

export type ProjectCreateFormData = z.infer<typeof projectCreateSchema>;

export const projectUpdateSchema = z.object({
  name: z.string().min(2, 'Project name must be at least 2 characters').max(100, 'Project name too long'),
  description: z.string().max(1000, 'Description too long').optional(),
});

export type ProjectUpdateFormData = z.infer<typeof projectUpdateSchema>;
