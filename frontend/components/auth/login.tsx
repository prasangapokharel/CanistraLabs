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
import { useLogin } from '@/hooks/api/useAuth';

const schema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(8, 'At least 8 characters'),
});

type FormData = z.infer<typeof schema>;

export function LoginForm() {
  const login = useLogin();
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { email: '', password: '' },
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit((d) => login.mutate(d))} className="space-y-4">
        {login.isError && (
          <Alert variant="destructive">
            <AlertDescription>{handleApiError(login.error)}</AlertDescription>
          </Alert>
        )}

        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" autoComplete="email" {...field} />
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
                <Input type="password" autoComplete="current-password" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit" className="w-full" disabled={login.isPending}>
          {login.isPending ? 'Signing in…' : 'Sign in'}
        </Button>

        <p className="text-center text-sm text-muted-foreground">
          <Link href="/auth/forgot-password" className="underline underline-offset-4">
            Forgot password?
          </Link>
        </p>

        <p className="text-center text-sm text-muted-foreground">
          No account?{' '}
          <Link href="/auth/signup" className="text-primary underline-offset-4 hover:underline">
            Sign up
          </Link>
        </p>
      </form>
    </Form>
  );
}
