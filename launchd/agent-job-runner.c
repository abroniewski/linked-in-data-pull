/* Main executable of "Agent Job Runner.app".
 *
 * Runs one job script and nothing else: the script must be an executable file inside ~/CODE_Repositories.
 * It starts /bin/zsh SCRIPT ARGS... as a child, waits for it, and exits with its status. It does not touch
 * the environment or working directory (the job script sets those up itself).
 *
 * It is a compiled program on purpose. If the app's executable were a shell script, macOS would attribute
 * permissions to the shell instead of to this app. macOS permissions (for example "files managed by
 * Google Drive") are granted to this app once, and every job started through it inherits them.
 */
#include <limits.h>
#include <spawn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

extern char **environ;

int main(int argc, char **argv) {
    const char *home = getenv("HOME");
    if (argc < 2 || !home) {
        fprintf(stderr, "agent-job-runner: usage: open -W -a APP --args SCRIPT [ARGS...] (HOME must be set)\n");
        return 64;
    }
    char root[PATH_MAX], job[PATH_MAX], base[PATH_MAX];
    snprintf(base, sizeof base, "%s/CODE_Repositories", home);
    if (!realpath(base, root)) { fprintf(stderr, "agent-job-runner: no %s\n", base); return 66; }
    if (!realpath(argv[1], job)) { fprintf(stderr, "agent-job-runner: no such script: %s\n", argv[1]); return 66; }
    size_t n = strlen(root);
    if (strncmp(job, root, n) != 0 || job[n] != '/') {
        fprintf(stderr, "agent-job-runner: refused, outside ~/CODE_Repositories: %s\n", job);
        return 64;
    }
    struct stat st;
    if (stat(job, &st) != 0 || !S_ISREG(st.st_mode) || access(job, X_OK) != 0) {
        fprintf(stderr, "agent-job-runner: not an executable file: %s\n", job);
        return 66;
    }
    char **args = calloc((size_t)argc + 2, sizeof *args);
    if (!args) return 70;
    args[0] = "/bin/zsh";
    args[1] = job;
    for (int i = 2; i < argc; i++) args[i] = argv[i];
    pid_t pid;
    if (posix_spawn(&pid, "/bin/zsh", NULL, NULL, args, environ) != 0) {
        perror("agent-job-runner: spawn");
        return 71;
    }
    int status = 0;
    if (waitpid(pid, &status, 0) < 0) return 72;
    return WIFEXITED(status) ? WEXITSTATUS(status) : 128 + WTERMSIG(status);
}
