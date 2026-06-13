'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import Link from 'next/link';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { handleApiError } from '@/lib/apiClient';
import { useSignup } from '@/hooks/api/useAuth';

const schema = z
  .object({
    email: z.string().email(),
    username: z.string().min(3).max(20).regex(/^[a-zA-Z0-9_-]+$/),
    password: z.string().min(8),
    confirm: z.string(),
  })
  .refine((d) => d.password === d.confirm, { message: 'Passwords must match', path: ['confirm'] });

type FormData = z.infer<typeof schema>;

export function SignupForm() {
  const signup = useSignup();
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { email: '', username: '', password: '', confirm: '' },
  });

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit((d) =>
          signup.mutate({ email: d.email, username: d.username, password: d.password })
        )}
        className="space-y-4"
      >
        {signup.isError && (
          <Alert variant="destructive">
            <AlertDescription>{handleApiError(signup.error)}</AlertDescription>
          </Alert>
        )}

        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="username"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Username</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Password</FormLabel>
              <FormControl>
                <Input type="password" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="confirm"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Confirm password</FormLabel>
              <FormControl>
                <Input type="password" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit" className="w-full" disabled={signup.isPending}>
          {signup.isPending ? 'Creating account…' : 'Create account'}
        </Button>

        <p className="text-center text-sm text-muted-foreground">
          Have an account?{' '}
          <Link href="/auth/login" className="text-primary underline-offset-4 hover:underline">
            Sign in
          </Link>
        </p>
      </form>
    </Form>
  );
}
