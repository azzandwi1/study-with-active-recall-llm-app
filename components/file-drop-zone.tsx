"use client"

import { useState, useCallback } from "react"
import { useDropzone } from "react-dropzone"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Upload, FileText, X } from "lucide-react"
import { motion } from "framer-motion"

interface FileDropZoneProps {
  onFileSelect: (file: File) => void
}

export function FileDropZone({ onFileSelect }: FileDropZoneProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (file) {
      setSelectedFile(file)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
    },
    maxFiles: 1,
    multiple: false,
  })

  const handleUpload = () => {
    if (selectedFile) {
      onFileSelect(selectedFile)
    }
  }

  const handleRemove = () => {
    setSelectedFile(null)
  }

  return (
    <div className="space-y-4">
      <Card
        {...getRootProps()}
        className={`rounded-2xl border-2 border-dashed cursor-pointer transition-all duration-300 ${
          isDragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-muted/50"
        }`}
      >
        <CardContent className="p-8">
          <input {...getInputProps()} />
          <div className="text-center space-y-4">
            <motion.div animate={isDragActive ? { scale: 1.1 } : { scale: 1 }} transition={{ duration: 0.2 }}>
              <Upload className="h-12 w-12 text-muted-foreground mx-auto" />
            </motion.div>

            {isDragActive ? (
              <div>
                <p className="text-lg font-medium text-primary">Lepaskan file di sini</p>
                <p className="text-sm text-muted-foreground">File PDF akan diupload</p>
              </div>
            ) : (
              <div>
                <p className="text-lg font-medium text-foreground">Drag & drop file PDF di sini</p>
                <p className="text-sm text-muted-foreground">atau klik untuk memilih file</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {selectedFile && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
          <Card className="rounded-xl">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText className="h-8 w-8 text-primary" />
                  <div>
                    <p className="font-medium text-foreground">{selectedFile.name}</p>
                    <p className="text-sm text-muted-foreground">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button onClick={handleUpload} size="sm" className="rounded-lg">
                    Proses File
                  </Button>
                  <Button onClick={handleRemove} variant="ghost" size="sm" className="rounded-lg">
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  )
}
