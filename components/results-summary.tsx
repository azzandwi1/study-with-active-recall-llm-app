"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckCircle, FileText, Clock, Target, ArrowRight } from "lucide-react"
import Link from "next/link"
import { motion } from "framer-motion"

interface ResultsSummaryProps {
  result: {
    success: boolean
    extractedText: string
    wordCount: number
    flashcardsGenerated: number
    processingTime: number
  }
}

export function ResultsSummary({ result }: ResultsSummaryProps) {
  return (
    <Card className="rounded-2xl border-0 shadow-lg bg-gradient-to-br from-emerald-50 to-emerald-100 dark:from-emerald-950/20 dark:to-emerald-900/20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-emerald-700 dark:text-emerald-300">
          <CheckCircle className="h-5 w-5" />
          Konten Berhasil Diproses!
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="text-center p-4 bg-white/50 dark:bg-black/20 rounded-xl"
          >
            <FileText className="h-8 w-8 text-primary mx-auto mb-2" />
            <p className="text-2xl font-bold text-foreground">{result.wordCount}</p>
            <p className="text-sm text-muted-foreground">Kata Diekstrak</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="text-center p-4 bg-white/50 dark:bg-black/20 rounded-xl"
          >
            <Target className="h-8 w-8 text-accent mx-auto mb-2" />
            <p className="text-2xl font-bold text-foreground">{result.flashcardsGenerated}</p>
            <p className="text-sm text-muted-foreground">Flashcard Dibuat</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.3 }}
            className="text-center p-4 bg-white/50 dark:bg-black/20 rounded-xl"
          >
            <Clock className="h-8 w-8 text-secondary mx-auto mb-2" />
            <p className="text-2xl font-bold text-foreground">2.3s</p>
            <p className="text-sm text-muted-foreground">Waktu Proses</p>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.4 }}
          className="text-center"
        >
          <p className="text-muted-foreground mb-4">
            Flashcard Anda siap! Mulai belajar dengan metode Active Recall sekarang.
          </p>
          <Link href="/learn">
            <Button size="lg" className="rounded-xl gap-2">
              Mulai Belajar
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </motion.div>
      </CardContent>
    </Card>
  )
}
