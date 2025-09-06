"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Loader2 } from "lucide-react"
import { motion } from "framer-motion"

interface ProgressIndicatorProps {
  progress: number
  currentStep: string
}

export function ProgressIndicator({ progress, currentStep }: ProgressIndicatorProps) {
  return (
    <Card className="rounded-2xl border-0 shadow-lg">
      <CardContent className="p-6">
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <Loader2 className="h-5 w-5 text-primary animate-spin" />
            <h3 className="text-lg font-semibold text-foreground">Memproses Konten</h3>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{currentStep}</span>
              <span className="text-sm font-medium text-foreground">{progress}%</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>

          <div className="grid grid-cols-3 gap-4 text-center text-sm">
            <motion.div
              className={`p-2 rounded-lg ${progress >= 25 ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"}`}
              animate={progress >= 25 ? { scale: [1, 1.05, 1] } : {}}
              transition={{ duration: 0.3 }}
            >
              Ekstraksi
            </motion.div>
            <motion.div
              className={`p-2 rounded-lg ${progress >= 60 ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"}`}
              animate={progress >= 60 ? { scale: [1, 1.05, 1] } : {}}
              transition={{ duration: 0.3 }}
            >
              Pembuatan
            </motion.div>
            <motion.div
              className={`p-2 rounded-lg ${progress >= 100 ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"}`}
              animate={progress >= 100 ? { scale: [1, 1.05, 1] } : {}}
              transition={{ duration: 0.3 }}
            >
              Selesai
            </motion.div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
