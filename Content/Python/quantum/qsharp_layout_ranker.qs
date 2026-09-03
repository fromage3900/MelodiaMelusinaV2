namespace QuantumGameplay.Experiment {
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Math;

    function CandidateScore(difficulty : Double, spacing : Double) : Double {
        let balance = 1.0 - AbsD(difficulty - 0.75);
        let spacingScore = 1.0 - AbsD(spacing - 0.55);
        return MaxD(0.0, balance * 0.6 + spacingScore * 0.4);
    }

    // Score-weighted measurement. Prepares |0> with probability
    // sA/(sA+sB) and |1> with sB/(sA+sB) using a single Y rotation whose
    // angle is the score ratio, then measures once. The measured result IS
    // the pick -- a genuine quantum collapse weighted by score, not a
    // deterministic tie-break with a decorative qubit.
    //
    // theta = 2 * atan2(sqrt(sB), sqrt(sA))  =>  P(|0>) = cos^2(theta/2)
    //       = sA/(sA+sB), P(|1>) = sB/(sA+sB).
    operation PickBestCandidate(difficultyA : Double, spacingA : Double, difficultyB : Double, spacingB : Double) : Result {
        use q = Qubit();

        let scoreA = CandidateScore(difficultyA, spacingA);
        let scoreB = CandidateScore(difficultyB, spacingB);
        let theta = 2.0 * ArcTan2(Sqrt(scoreB), Sqrt(scoreA));

        Ry(theta, q);
        let measurement = M(q);
        ResetAll([q]);
        return measurement;
    }
}
