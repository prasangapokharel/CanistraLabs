'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
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
import { useCreateProject } from '@/hooks/api/useProjects';
import { handleApiError } from '@/lib/apiClient';
import { DEFAULT_FILES, serializeProjectFiles } from '@/lib/project-files';

const schema = z.object({
  name: z.string().min(1, 'Name required').max(100),
});

type FormData = z.infer<typeof schema>;

export default function NewProjectPage() {
  const router = useRouter();
  const createProject = useCreateProject();
  const [uploadError, setUploadError] = useState<string | null>(null);

  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { name: '' },
  });

  const onSubmit = async (data: FormData) => {
    const project = await createProject.mutateAsync({
      name: data.name,
      language: 'html',
      code_content: serializeProjectFiles(DEFAULT_FILES),
    });
    router.push(`/dashboard/projects/${project.id}`);
  };

  const onUploadFolder = async (e: React.ChangeEvent<HTMLInputElement>) => {
    setUploadError(null);
    const fileList = e.target.files;
    if (!fileList?.length) return;

    const files: Record<string, string> = { ...DEFAULT_FILES };
    for (const file of Array.from(fileList)) {
      const path = file.webkitRelativePath
        ? file.webkitRelativePath.split('/').slice(1).join('/') || file.name
        : file.name;
      if (/\.(html|css|js|json|txt|svg)$/i.test(path)) {
        files[path] = await file.text();
      }
    }

    const name = form.getValues('name') || 'Uploaded project';
    try {
      const project = await createProject.mutateAsync({
        name,
        language: 'html',
        code_content: serializeProjectFiles(files),
      });
      router.push(`/dashboard/projects/${project.id}`);
    } catch (err) {
      setUploadError(handleApiError(err));
    }
    e.target.value = '';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">New project</h1>
        <p className="text-sm text-muted-foreground">Start blank or upload a folder of files</p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          {createProject.isError && (
            <Alert variant="destructive">
              <AlertDescription>{handleApiError(createProject.error)}</AlertDescription>
            </Alert>
          )}

          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Project name</FormLabel>
                <FormControl>
                  <Input placeholder="My website" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button type="submit" disabled={createProject.isPending}>
            {createProject.isPending ? 'Creating…' : 'Create and open editor'}
          </Button>
        </form>
      </Form>

      <div className="border-t pt-4">
        <p className="text-sm text-muted-foreground mb-2">Or upload an existing site</p>
        <label>
          <input
            type="file"
            multiple
            // @ts-expect-error webkitdirectory is non-standard
            webkitdirectory=""
            className="hidden"
            onChange={onUploadFolder}
          />
          <Button
            variant="outline"
            type="button"
            disabled={createProject.isPending}
            render={<span />}
          >
            Upload folder
          </Button>
        </label>
        <p className="text-xs text-muted-foreground mt-2">
          HTML, CSS, JS files. Must include index.html.
        </p>
        {uploadError && (
          <Alert variant="destructive" className="mt-2">
            <AlertDescription>{uploadError}</AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  );
}
