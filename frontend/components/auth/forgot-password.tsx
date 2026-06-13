"use client"

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Mail, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react'
import { z } from 'zod'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Alert, AlertDescription } from '@/components/ui/alert'

import { useForgotPassword } from '@/hooks/api/useAuth'

const forgotPasswordSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address'),
})

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>

export function ForgotPasswordForm() {
  const [isSubmitted, setIsSubmitted] = useState(false)
  const forgotPasswordMutation = useForgotPassword()

  const form = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: '',
    },
  })

  const onSubmit = async (data: ForgotPasswordFormData) => {
    try {
      await forgotPasswordMutation.mutateAsync({ email: data.email })
      setIsSubmitted(true)
    } catch {
      // Error handling is done by the hook
    }
  }

  const isLoading = forgotPasswordMutation.isPending
  const hasError = forgotPasswordMutation.isError && !isSubmitted

  if (isSubmitted) {
    return (
      <div className="space-y-6">
        <Alert variant="destructive">
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription>
            <strong>Check your email!</strong><br />
            If an account with that email exists, we&apos;ve sent you password reset instructions.
          </AlertDescription>
        </Alert>

        <div className="space-y-4 text-center">
          <div className="space-y-2">
            <p>Didn&apos;t receive the email? Check your spam folder.</p>
            <p>Still having trouble? Contact our support team.</p>
          </div>
          
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setIsSubmitted(false)
              forgotPasswordMutation.reset()
              form.reset()
            }}
            className="w-full"
          >
            Try a different email
          </Button>
        </div>
      </div>
    )
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* General Error Alert */}
        {hasError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {forgotPasswordMutation.error?.message || 'Something went wrong. Please try again.'}
            </AlertDescription>
          </Alert>
        )}

        {/* Email Field */}
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email Address</FormLabel>
              <FormControl>
                <div className="relative">
                  <Input
                    type="email"
                    placeholder="Enter your email address"
                    disabled={isLoading}
                    autoComplete="email"
                    autoFocus
                    {...field}
                  />
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Submit Button */}
        <Button
          type="submit"
          className="w-full"
          disabled={isLoading}
        >
          {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isLoading ? 'Sending reset link...' : 'Send reset link'}
        </Button>

        {/* Security Notice */}
        <div className="text-center">
          <p className="text-xs text-muted-foreground">
            For security reasons, we&apos;ll only send reset instructions to verified email addresses.
            The reset link will expire in 1 hour.
          </p>
        </div>
      </form>
    </Form>
  )
}
